# Muserve Server

## Database Schema

![database schema](./database.png)

## Configuration

The app will check the following locations for a config in order. If a config
doesn't yet exist, please make a copy of the example config.

```
~/.config/muserve/muserve.json
```

or

```
./muserve.json
```

Alternately, you can use `--conf [path to conf]` to specify a custom location.
