from apps.youtube_summarizer.summarizer import YoutubeSummarizer
import time
import json
current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
file_name = f"{current_time}.md"


if __name__ == '__main__':
    file = open("2023-04-17_10-20-46.md", "r")
    data = json.loads(file.read())
    summarizer = YoutubeSummarizer('na', debug=True)
    summary = data.get('summary')
    print(len(summary))
    reduction = summarizer.reduction(summary, 1650)
    print(reduction)
    print(len(reduction))
    # from pprint import pprint
    # pprint(data)
    # yt = YoutubeSummarizer('https://www.youtube.com/watch?v=UsWB1XodUKA', debug=True)
    # with open(file_name, 'w') as file:
    #     file.write(json.dumps(yt.get_youtube_summary()))