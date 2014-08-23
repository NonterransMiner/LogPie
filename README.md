LogPie
======

LogLab is a log reader generator, it's main purpose is use builtin frameworks and a given pattern
to generate a reader, which will parse each record in the log file into a `dict` object for further use.

LogLab is a part of our main target, build a log-based predirective tool to find out potential fault in a running system.

## Usage

**Now the generator and the generated reader only support some situation.**

To generate a reader:

```shell
python3 reader/generate.py logsys pattern
```

where logsys should be `log4j` or `systemd`.

for pattern, see offical docmentions & the log system's configurations.

> systemd is now just for test, see #3 and [wiki:Systemd][wiki-systemd] for more information.
> log4j's MDC & NDC is not supported yet, see #4

the generated file, like reader/gen/logsys_suffix.py

suffix should be `time.time() % 10000`, if taken, then increase by 1 and try again.

Use:

```shell
python3 /reader/gen/logsys_suffix.py file
```

to analyse the given file, and **returns nothing**, unless edit it's `main()` on your own.

[wiki-systemd]: https://gitlab.com/nonterransminer/logpie/wikis/Systemd
