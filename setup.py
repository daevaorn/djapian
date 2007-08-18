from distutils.core import setup
setup( name="Djapian", version="1.0",
       author='Rafael "SDM" Sierra', author_email="rafaeljsg14@gmail.com",
       packages=[ "djapian", "djapian.backend" ], package_dir={ "djapian": "src" },
       scripts=['src/run_djapian.py']
     )
