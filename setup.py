from setuptools import setup, find_packages

setup(
    name='md2card',
    version='0.1.0',
    description='Convert articles to Xiaohongshu style image cards',
    author='Your Name',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Pillow>=8.0.0'
    ],
    entry_points={
        'console_scripts': [
            'md2card=md2card.cli:main'
        ]
    }
)
