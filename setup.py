from setuptools import setup, find_packages

setup(
    name="billgpt-websockets",
    packages=find_packages("billgpt"),
    package_dir={"": "billgpt"},
    install_requires=[
        "Flask",
        "flask_socketio",
    ],
)
