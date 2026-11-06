`against`: a pull request stacked on another no longer duplicates its names
once both have merged main again since. Then neither holds the other's head,
and git names main's tip as one of their merge bases, so the stack's shared
commits were read as each one's own (#265 against #267 to #270)
