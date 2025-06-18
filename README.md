[![Build Status](https://github.com/uw-it-aca/canvas-analytics/actions/workflows/cicd.yml/badge.svg)](https://github.com/uw-it-aca/canvas-analytics/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/canvas-analytics/badge.svg?branch=main)](https://coveralls.io/github/uw-it-aca/canvas-analytics?branch=main)

# Canvas Analytics

The Canvas Analytics project contains an automated ETL workflow for extracting assignment and participation analytics from the Canvas API, as well as, an API for accessing harvested analytics.

Every weekend, batches of asyncronous jobs query the Canvas API to collect student level assignment and participation analytics. Additionally, user and course provisioning reports are loaded, parsed, and archived in the database. Jobs may be viewed and managed via a [light weight admin web interface](https://analytics.apps.canvas.uw.edu/admin).

The internally facing Canvas Analytics API provides an interface for requesting harvested analytics. See the [detailed api documentation](https://analytics.apps.canvas.uw.edu/api) for information about API usage.
