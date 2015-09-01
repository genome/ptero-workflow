This test failed on commit a008481 and began passing after 51af1d7 (which
merged a large development branch).

It was discovered when attempting to write a benchmarking workflow that had 3
types of steps:

1. A start step that recorded the initial timestamp
2. A parallelBy step that just called sleep.
3. A stop step that calculated the run time of the net by subtracting the
   current timestamp from the initial timestamp.
