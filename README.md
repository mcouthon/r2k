# R2K (RSS to Kindle)

A tool that lets you periodically send articles received from an RSS feed to your Kindle.
`r2k` allows you to track your favorite RSS/Atom feeds, and send cleaned versions of them to your
Kindle.

It currently does this by sending you email messages through the 
[PushToKindle](http://pushtokindle.com/) service. The service cleans up the articles, removing any
ads and fluff, and you're left with only the text and images.

Future releases are likely to include alternatives to using PushToKindle. The first such plugin
will use a dockerized version of the [Mercury-Parser](https://github.com/postlight/mercury-parser).  

[Installation](#installation)
[Usage](#usage)

## Installation
If you are using Poetry, add `r2k` to your `pyproject.toml` file by using:
```bash
poetry add r2k
```

If not, you can use `pip`:

```
pip install r2k
```

## Usage

### Preparations

#### If you're using PushToKindle (PTK)

The free version of PTK only allows for 25 articles to be sent using their service. After this,
you'll have to become their "sustainer" (for as low as 1$/month) on Patreon 
[here](https://www.patreon.com/bePatron?c=1946606).

Before using `r2k` with PTK you need to:

1. Know your kindle email address (find it [here](https://www.amazon.com/mycd), under 
"Preferences" -> "Personal Document Settings").

2. Add `kindle@fivefilters.org` to the list of approved email senders (in the same place in 
Amazon's settings).

### Set up your configuration file

Most of what `r2k` does involves the configuration file, in which the feeds you're subscribed to
are kept, as well as some other data.

After installation, run:

```bash
r2k config init [-p CONFIG_PATH] 
```

The default location for the config YAML file is in `~/.r2k/config.yml`.

During the init you'll be asked several questions (like your kindle email address).

To see your configuration run:

```bash
r2k config show [-p CONFIG_PATH]
```

### Add some RSS subscriptions

#### Using an OPML file

The [OPML](https://en.wikipedia.org/wiki/OPML) format is widely used in the RSS/Atom world 
(as well as in podcasting and other areas) to represent a collection of feeds. You can export your 
existing subscriptions from most feed readers into an OPML file.

To load all of your subscriptions in one move run:

```bash
r2k feed import PATH_TO_OPML_FILE
```

#### Manually adding feeds

If you don't have an OPML export, or just want to add a single feed you can run:

```bash
r2k feed add -t FEED_TITLE -u FEED_URL
```

If the `FEED_URL` is a proper RSS feed (i.e. an actual XML feed URL), it will be added as is.
If the `FEED_URL` is a regular URL, `r2k` will attempt to find the RSS feed by analyzing the page
source. In the case of multiple candidates (e.g. WordPress content feed and comment feed), you will
be presented with a list of choices.

### Send updates to your Kindle

Right now the "periodical" part of `r2k` is not yet operational. In order to send updates to your
Kindle you'll have to run:

```bash
r2k kindle send [-f FEED_TITLE]
```

If you don't pass the `-f/--feed-title` option, updates will be sent for all of your subscriptions.

The first time that `kindle send` is run for any feed, you will be presented with a list of all the 
available articles in the feed (note that RSS feeds usually only keep a subset of the most recent
entries), and will be asked to choose the last one you've already read. This is to avoiding sending
you any article you've already consumed.
 