# Changelog

## changes in 0.4.1
- fixed [#1](https://github.com/raspishake/rsudp/issues/1) which caused the writing module to crash on some machines
- added a module that posts to twitter in the event of an alert, and can also post screenshots saved by the plot module
- fixed [#2](https://github.com/raspishake/rsudp/issues/2) which caused an error at 28>1 30>1 and 31>1 month rollovers
    - should also address issues arising from leap second addition
