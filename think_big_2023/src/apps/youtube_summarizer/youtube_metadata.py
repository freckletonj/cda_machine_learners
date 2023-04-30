from xml.etree import ElementTree
from html import unescape
import requests
import re
import json
from bs4 import BeautifulSoup


class YouTubeMetaData:
    """
    Used to get YouTube video metadata.

    @param url: The YouTube video URL
    """

    def __init__(self, url):
        self.url = url
        self._soup = None
        self._initial_player_response = None
        self._initial_data = None
        self._title = None
        self._description = None
        self._chapters = None
        self._captions_url = None
        self._captions = None
        self._grouped_transcripts = None

    @staticmethod
    def seconds_to_timestamp(seconds):
        seconds = round(float(seconds))
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def time_to_seconds(time_str):
        time_parts = list(map(int, time_str.split(':')))
        if len(time_parts) == 3:
            h, m, s = time_parts
        elif len(time_parts) == 2:
            h = 0
            m, s = time_parts
        else:
            raise ValueError(f"Invalid time format: {time_str}")
        return h * 3600 + m * 60 + s

    @staticmethod
    def if_tuple_get_first(t):
        if isinstance(t, tuple):
            return t[0]
        return t

    @property
    def soup(self) -> BeautifulSoup:
        if not bool(self._soup):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
            }
            response = requests.get(self.url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            self._soup = soup
        return self._soup

    @property
    def initial_player_response(self) -> dict:
        if not bool(self._initial_player_response):
            script = self.soup.find('script', string=lambda x: x and 'var ytInitialPlayerResponse' in x)
            if not script:
                raise ValueError('Failed to find ytInitialPlayerResponse in the page source.')

            json_str = re.search(r'var ytInitialPlayerResponse = ({.*?});', script.string).group(1)
            data = json.loads(json_str)
            self._initial_player_response = data
        return self._initial_player_response

    @property
    def initial_data(self) -> dict:
        if not bool(self._initial_data):
            script = self.soup.find('script', string=lambda x: x and 'var ytInitialData' in x)
            if not script:
                raise ValueError('Failed to find ytInitialData in the page source.')

            json_str = re.search(r'var ytInitialData = ({.*?});', script.string).group(1)
            data = json.loads(json_str)
            self._initial_data = data
        return self._initial_data

    @property
    def title(self):
        if not bool(self._title):
            self._title = self.initial_player_response.get('videoDetails', {}).get('title')
        return self._title

    @property
    def description(self):
        if not bool(self._description):
            self._description = self.initial_player_response.get('videoDetails', {}).get('shortDescription')
        return self._description

    @property
    def chapters(self):
        if not bool(self._chapters):
            engagement_panels = self.initial_data.get('engagementPanels')
            chapters = []
            for panel in engagement_panels:
                contents = panel.get('engagementPanelSectionListRenderer', {}).get('content', {}).get(
                    'macroMarkersListRenderer', {}).get('contents', [])
                for c in contents:
                    title = c.get('macroMarkersListItemRenderer', {}).get('title', {}).get('simpleText'),
                    timestamp = c.get('macroMarkersListItemRenderer', {}).get('timeDescription', {}).get('simpleText'),
                    a11y_label = c.get('macroMarkersListItemRenderer', {}).get('timeDescriptionA11yLabel'),
                    relative_url = c.get('macroMarkersListItemRenderer', {}).get('onTap', {}).get('commandMetadata',
                                                                                                  {}).get(
                        'webCommandMetadata', {}).get('url')

                    if not all([title, timestamp, a11y_label, relative_url]):
                        continue

                    chapter = {
                        'title': self.if_tuple_get_first(title),
                        'timestamp': self.if_tuple_get_first(timestamp),
                        'timestamp_seconds': self.time_to_seconds(self.if_tuple_get_first(timestamp)),
                        'a11y_label': self.if_tuple_get_first(a11y_label),
                        'relative_url': self.if_tuple_get_first(relative_url),
                    }
                    chapters.append(chapter)
            self._chapters = chapters
        return self._chapters

    @property
    def captions_url(self):
        if not bool(self._captions_url):
            captions_tracks = self.initial_player_response.get('captions', {}).get('playerCaptionsTracklistRenderer',
                                                                                   {})
            if not captions_tracks:
                raise ValueError('Failed to find captions in the page source.')
            audio_tracks = captions_tracks.get('audioTracks', [])
            if not audio_tracks:
                raise ValueError('Failed to find audio tracks in the page source.')
            caption_track_index = audio_tracks[0].get('captionTrackIndices')[0]
            caption_tracks = captions_tracks.get('captionTracks', [])
            if not caption_tracks:
                raise ValueError('Failed to find caption tracks in the page source.')
            self._captions_url = caption_tracks[caption_track_index].get('baseUrl')
        return self._captions_url

    @property
    def captions(self):
        if not bool(self._captions):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
            }
            response = requests.get(self.captions_url, headers=headers)
            self._captions = [{'text': unescape(c.text), **c.attrib} for c in ElementTree.fromstring(response.text)]
        return self._captions

    @property
    def has_chapters(self):
        return bool(self.chapters)

    def grouped_transcripts(self):
        """Get grouped transcripts by chapters."""
        if not self.has_chapters:
            raise ValueError('This video does not have chapters.')

        grouped_transcripts = []
        chapter_index = 0
        # Copy the transcripts list
        transcripts = list(self.captions)

        for chapter in self.chapters:
            current_chapter_start = chapter['timestamp_seconds']

            # Check if we have reached the next chapter
            if chapter_index + 1 < len(self.chapters):
                next_chapter_start = self.chapters[chapter_index + 1]['timestamp_seconds']
            else:
                next_chapter_start = float('inf')

            # Group transcripts by chapter
            chapter_transcripts = []
            while transcripts and current_chapter_start <= float(transcripts[0]['start']) < next_chapter_start:
                chapter_transcripts.append(transcripts.pop(0))

            # Append the chapter object to the results
            grouped_transcripts.append({
                'title': chapter['title'],
                'transcripts': ' '.join(c['text'] for c in chapter_transcripts)
            })
            chapter_index += 1
        self._grouped_transcripts = grouped_transcripts
        return self._grouped_transcripts

    def json(self):
        return {
            'title': self.title,
            'description': self.description,
            'chapters': self.chapters,
            'transcripts': self.captions
        }

    def __repr__(self):
        return str(f'<YouTubeMetaData: {self.title}>')

    def __str__(self):
        return str(self.title)

    def __dict__(self):
        return self.json()
