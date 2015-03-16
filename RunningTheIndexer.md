After setup the project and configure the models, you just need to run:
> `python manage.py index`

And it will wait for changes in the models and update the index database

You can also use those options:

  * `--verbose` - Will print every change into the database (default: No)
  * `--daemonize` - Fork the process to background, avoid use with `--verbosity` or your terminal will be useless (default: No)
  * `--time-out` - Time to wait before each verification for updates (default: 10)
  * `--rebuild` - Erase the database and starts a new one
  * `--loop` - If you want to keep indexer running in foreground (whitout --daemonize), use this option, this will hang your terminal, which means indexer is running