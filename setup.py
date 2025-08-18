from setuptools import setup, find_packages

setup(
    name="EnvironmentDev_MISA",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'environment-dev-gui=gui.main:main',
        ],
    },
    install_requires=[
        'PySide6',
        # Add other dependencies here as they are identified
        # e.g., 'requests', 'pyyaml'
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to manage and configure development environments.",
    long_description=open('README.md', encoding='utf-8').read() if open('README.md', 'r', encoding='utf-8') else '',
    long_description_content_type="text/markdown",
    url="https://github.com/Misael-art/EnvironmentDev_MISA",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", # Or your chosen license
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6', # Or your minimum required version
)