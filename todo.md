# TODO LIST

- [ ] Use kindlegen to create a MOBI from the EPUB (why?)
- [ ] Split large ebooks into multiple smaller ones
- [ ] Validate existence of docker early, and fail with nice message
- [ ] Research whether it's possible to use the Mercury Parser without docker (perhaps a gem/npm?)
- [ ] Consider sending large files using Google Drive attachment, to avoid 25MB gmail limit
- [ ] Gauge size of EPUB archive in a more intelligent way than just limiting number of articles
- [ ] Make more parts of the app configurable
    - [ ] Max number of articles per ebook
    - [ ] SMTP server (currently only GMAIL)

### Docs
- [ ] Update Mercury Parser section
- [ ] Better handling of initial config 
    - [ ] Explain how to get a google app password
