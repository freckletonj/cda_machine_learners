from apps.youtube_summarizer.map_reduce_continue import MapReduceContinue
from apps.youtube_summarizer.youtube_metadata import YouTubeMetaData


class YoutubeSummarizer:
    def __init__(self, yt_url, debug=False):
        self.yt = YouTubeMetaData(yt_url)
        self.mrc = MapReduceContinue(debug=debug)
        self._formatted_transcripts = None
        self._grouped_transcripts = None
        self.debug = debug

    def chapter_aware_summarize(self):
        if not self.yt.has_chapters:
            raise ValueError("This video does not have chapters")
        grouped_transcripts = self.yt.grouped_transcripts()
        for chapter in grouped_transcripts:
            chapter['summary'] = self.mrc.summarize(chapter["transcripts"], chapter=chapter['title'])
        formatted_summary = f''
        for chapter in grouped_transcripts:
            formatted_summary += f'## {chapter["title"]}\n{chapter["summary"]}\n*****\n'
        return formatted_summary

    def summarize(self):
        if self.yt.chapters:
            if self.debug:
                print(f"Summarizing by chapter")
            return self.chapter_aware_summarize()
        else:
            if self.debug:
                print(f"Summarizing whole transcript")
            return f'{self.mrc.summarize(" ".join([t["text"] for t in self.yt.captions]))}'

    def reduction(self, text, max_length=1650, max_iterations=3, iteration=0):
        if iteration > max_iterations:
            # TODO: Update this when we aren't paying for an API to run the model
            print(f"Max iterations reached, returning summary of length {len(text)} characters")
            return text

        if len(text) > max_length:
            print(f"Reducing summary from {len(text)} to {max_length} characters")
            return self.reduction(self.mrc.summarize(text), max_length, max_iterations, iteration + 1)
        return text

    def get_youtube_summary(self):
        data = {
            'title': self.yt.title,
            'summary': self.summarize(),
        }
        max_len = 1900
        if len(data['summary']) > max_len:
            data['reduction'] = self.reduction(data['summary'], max_len)
        return data

    def __repr__(self):
        return f"<YoutubeSummarizer: {self.yt.title}>"
