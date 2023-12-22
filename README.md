# Tab Grabber

Tab Grabber is a script intended to convert online video music tabs into a single document, removing the need to constantly pause and move the video to practice.

To use, run [tabgrab.py](tabgrab.py) and enter the video URL, when the tab appears in the video (to account for fade ins, intros, etc.), and whether or not to manually select the portion of the video where the tab is located.

Tab Grabber uses computer vision to determine the position of the tab and when it switches pages, so manual adjustments may be needed for unconventional tab formats.

Example result (cropped):
![ExampleSheet](Examples/PutYourHeadOnMyShoulderEasyVersionPaulAnkaFingerstyleGuitarTABChordsLyrics.jpg)
Original from Kenneth Acoustic on YouTube (https://www.youtube.com/watch?v=z7-maOwsoy0)