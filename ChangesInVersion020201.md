## Changes in Djapian 2.2.1 ##

  * Added additional `index` commands parameters to enable transactions and flushing

### Major bug fixes ###

  * Large update queues now split by pages for less memory consumption
  * Disabled Xapian transactions by default - for index performance reasons