from setuptools import setup, find_packages

setup(
    name="netpulse",
    version="1.0.0",
    description="Network Traffic Analyzer, IDS & Troubleshooting Diagnostic Suite",
    author="Shanawaz Patel",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "scapy>=2.5.0",
        "rich>=13.0.0",
        "flask>=2.3.0",
        "flask-cors>=4.0.0"
    ],
    entry_points={
        "console_scripts": [
            "netpulse=netpulse.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Security",
        "Operating System :: OS Independent",
    ],
)
