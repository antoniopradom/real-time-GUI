from setuptools import setup, find_packages


def filter_lines(val):
    val = val.strip(' ')
    if val and not val.startswith('-r') and not val.startswith('#'):
        return True
    return False


def requirements_filter(fd):
    return list(filter(filter_lines, fd.read().split('\n')))


VERSION = '0.0.1'
DESCRIPTION = 'Python package for signal plotting using tk'
LONG_DESCRIPTION = 'Python package for signal plotting using tk with real time capabilities'
with open('requirements.txt', 'r') as fd:
    requirements = requirements_filter(fd)
install_requires = list(requirements)
# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="rtgui",
    version=VERSION,
    author="Antonio Prado",
    author_email="<jap2254@columbia.edu>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=install_requires,

    keywords=['python', 'tkinter', 'plotting', 'gui'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
