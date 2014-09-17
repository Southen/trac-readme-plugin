from setuptools import setup

setup(
    name='ReadmeRendererPlugin',
    version='0.1',
    description='Plugin to display README* files in Browse Source directory listings, and preview .md files as rendered Markdown',
    author='Southen',
    url='https://github.com/Southen/trac-readme-plugin',
    license='BSD',
    packages=['readme_renderer'],
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
    ],
    entry_points={
        'trac.plugins': 'readme_renderer = readme_renderer'
    },
    package_data={
        'readme_renderer': [
            'htdocs/*.css',
            'htdocs/*.js'
        ]
    }
)
