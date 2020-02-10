import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

deps = ['pygame',
        'click',
        'cython']

setuptools.setup(
    name="petvideo",
    version="1.0.0",
    author="Guillaume Binet",
    author_email="gbin@gootz.net",
    description="A screen emulator for Commodore PET.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gbin/petvideo",
    packages=setuptools.find_packages(),
    install_requires=deps,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: System :: Emulators",
        "Topic :: System :: Hardware",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
