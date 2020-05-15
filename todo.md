# TODO LIST

## Features

### Major Features
- [ ] Create a cron (or some other periodic process) to periodically check for updates
- [ ] Research whether it's possible to use the Mercury Parser without docker (perhaps a gem/npm?)

### Minor Features
- [ ] Gauge size of EPUB archive in a more intelligent way than just limiting number of articles
- [ ] Consider sending large files using Google Drive attachment, to avoid 25MB gmail limit

### Improvements
- [ ] Use kindlegen to create a MOBI from the EPUB (why?)
- [ ] Better, cleaner logs
- [ ] Validate existence of docker early, and fail with nice message
- [ ] Make more parts of the app configurable
    - [ ] Max number of articles per ebook
    - [ ] SMTP server (currently only GMAIL)

## Bug fixes

## Docs
- [ ] Update Mercury Parser section
- [ ] Better handling of initial config 
    - [ ] Explain how to get a google app password
