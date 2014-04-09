# PTero Workflow Service
[![Build Status](https://travis-ci.org/mark-burnett/ptero-workflow.svg?branch=master)](https://travis-ci.org/mark-burnett/ptero-workflow)
[![Coverage Status](https://coveralls.io/repos/mark-burnett/ptero-workflow/badge.png)](https://coveralls.io/r/mark-burnett/ptero-workflow)

This project provides the client facing API for the PTero Workflow system.
This system is designed to be a highly scalable replacement of the [legacy
Workflow](https://github.com/genome/tgi-workflow) system from [The Genome
Institute](http://genome.wustl.edu/).

The current implementation, which does not provide an easy to use API, easily
handles our production workflows with tens of thousands of nodes.  For
reference, it can be found in two parts:
[core](https://github.com/genome/ptero-core) and
[workflow](https://github.com/genome/ptero-workflow)

The workflows are driven using an implementation of [Petri
nets](https://en.wikipedia.org/wiki/Petri_net) with some extensions for
[color](https://en.wikipedia.org/wiki/Coloured_Petri_net) and token data.

The API is currently described
[here](https://github.com/mark-burnett/ptero-apis/blob/master/workflow.md).
The other existing components are: the [petri
core](https://github.com/mark-burnett/ptero-petri) service and a [forking shell
command](https://github.com/mark-burnett/ptero-shell-command-fork) service.


## Testing

To run tests:

    pip install tox
    tox
