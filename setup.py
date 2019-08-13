from setuptools import setup, find_packages

setup(
    name='namuplant',
    version='0.0.1',
    description='A bot for namu.wiki',
    long_description='',
    author='double-underscore',
    url='https://github.com/double-underscore/namu-plant',
    license='',
    packages=find_packages(),
    install_requires=['PySide2',
                      'psutil',
                      'requests',
                      'beautifulsoup4',
                      'pyperclip',
                      'keyboard',
                      'mouse']
)