from setuptools import setup, find_packages

setup(
    name="ai_stream_interact",
    version='0.0.1',
    author='Omar Aref',
    author_email='oa_dev_acc_92@hotmail.com',
    description='An model agnostic extensible package that allows for AI & LLM interactions on a video stream',
    long_description_content_type="text/markdown",
    packages=find_packages(),
    # install_requires=['opencv-python', 'pyautogui', 'pyaudio'],
    keywords=['python', 'ai', 'llm', 'artificial intelligence', 'large language models', 'nlp', 'natural language processing', 'video', 'video stream'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
    ]
)
