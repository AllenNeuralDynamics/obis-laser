import setuptools

with open("README.md", "r", newline="", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="obis_laser",
    version="0.0.1",
    author="Joshua Vasquez",
    author_email="joshua.vasquez@alleninstitute.org",
    description="a minimal python package for controlling Obis LS and LX lasers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AllenNeuralDynamics/obis-laser",
    license="MIT",
    keywords= ['driver', 'instrument', 'serial device'],
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.6',
    install_requires=['pyserial']
)
