# Video Silence Remover

The objective of this project is to create software capable of assisting in automatic video editing, with minimal human supervision. I have a video (in portuguese) that explains the project.

<p align="center">
  <a href="https://youtu.be/7ELvYSHCAc4"><img src="https://img.youtube.com/vi/7ELvYSHCAc4/maxresdefault.jpg"></a>
</p>

## How to Use

First of all, it needs [ImageMagick](https://imagemagick.org/script/download.php) installed in your system. I have used ImageMagick-7.0.10-Q16.

### Installing

1. From a terminal window, use "git clone https://github.com/lucaslattari/Video-Silence-Remover.git" command.
2. Run "pip install -r requirements.txt".

### Running

Run "python main.py video.mp4" from project folder. At the end of the program execution, the final.mp4 file will be created in the folder.

Command line arguments are presented:
![Program Arguments](https://universodiscreto.com/images/arguments.png)

## More Details

* (https://www.youtube.com/watch?v=7ELvYSHCAc4) - Youtube video explaining how the software works and the source code (in Brazilian Portuguese).
* (https://universodiscreto.com/2020/01/30/fiz-um-programa-que-edita-videos-pra-mim-parte-1/) - First part of a blog post that explains how the software works in the most updated version (in Brazilian Portuguese).

## Built With

* [pydub](https://github.com/jiaaro/pydub) - Manipulate audio with a simple and easy high level interface (http://pydub.com).
* [moviepy](https://zulko.github.io/moviepy/) - Python module for video editing.

## Contributing

Consider yourself welcome to contribute to the project!

## Authors

* **Lucas Lattari** - [universodiscreto](https://github.com/lucaslattari)

## Acknowledgments

* People who follow me on youtube and on the internet.
* **Douglas Lacerda** - [HermesPasser](https://github.com/HermesPasser) for helping to improve the initial code.
