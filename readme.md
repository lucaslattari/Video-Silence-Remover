# Video Silence Remover

The objective of this project is to create software capable of assisting in automatic video editing, with minimal human supervision. I have a video (in Portuguese) that explains the project.

<p align="center">
  <a href="https://youtu.be/7ELvYSHCAc4"><img src="https://img.youtube.com/vi/7ELvYSHCAc4/maxresdefault.jpg"></a>
</p>

## How to Use

First of all, you need to have [ImageMagick](https://imagemagick.org/script/download.php) installed on your system. I have used ImageMagick-7.0.10-Q16.

### Installing

1. Clone the repository with the following command: git clone https://github.com/lucaslattari/Video-Silence-Remover.git
2. Install the requirements with the following command: pip install -r requirements.txt

### Running

Run the following command from the project folder to execute the program: python main.py video.mp4

At the end of the program execution, the final.mp4 file will be created in the same folder.

## Disclaimer

This software has not been tested on Linux and may not work as expected. While efforts have been made to ensure compatibility with Windows, the software may not function properly on other operating systems. Use at your own risk.

## More Details

* [YouTube Video](https://www.youtube.com/watch?v=7ELvYSHCAc4) - A video explaining how the software works and the source code (in Brazilian Portuguese).
* [Blog Post](https://universodiscreto.com/2020/01/30/fiz-um-programa-que-edita-videos-pra-mim-parte-1/) - The first part of a blog post that explains how the software works in the most updated version (in Brazilian Portuguese).

## Built With

* [pydub](https://github.com/jiaaro/pydub) - A Python library for audio manipulation with a simple and easy high-level interface (http://pydub.com).
* [moviepy](https://zulko.github.io/moviepy/) - A Python library for video editing.

## Contributing

Feel free to contribute to the project!

## Authors

* **Lucas Lattari** - [universodiscreto](https://github.com/lucaslattari)

## Acknowledgments

* People who follow me on YouTube and on the internet.
* **Douglas Lacerda** - [HermesPasser](https://github.com/HermesPasser) for helping to improve the initial code.
