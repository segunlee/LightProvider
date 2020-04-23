from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.

include_files = [ 'lightcomics.json']

include = [ 'jinja2', 'jinja2.ext', 'Pillow']

buildOptions = dict(packages = [], excludes = [], include_files=include_files, includes=include)

base = 'Console'

executables = [
    Executable('lightcomics.py', base=base)
]

setup(name='LightComics',
      version = '1.0',
      description = 'devel',
      options = dict(build_exe = buildOptions),
      executables = executables)
