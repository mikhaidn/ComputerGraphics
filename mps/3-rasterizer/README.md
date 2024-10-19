https://cs418.cs.illinois.edu/website/mps/rasterizer.html


Implement the core parts of a simplified version of the WebGL API that we’ll be using for most other MPs. In particular,

Write a program that reads a .txt file and produces a .png file. It will be invoked as e.g. ./yourprogram exampleInput.txt, via a makefile.

Handle the input file keywords png, position 4 ..., color 3 ..., and drawArraysTriangles. See our notes on program state for tips on doing this well.

Implement the DDA algorithm, and the scanline algorithm which consists of repeated invocations of DDA. These algorithms are defined down to the pixel in almost all contexts, and should match the provided input files and their outputs very closely. Almost all successful submissions follow our DDA pseudocode and scanline diagram closely.

Implement division by 
w
w and viewport transformations. See our notes on algorithms for tips on doing this well.

