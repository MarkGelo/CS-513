# Probe Data Analysis
Spring 2021 CS 513 - Geospatial Vision / Visualization

## Group
Yutong Chen A20473032\
Yinting Hui A20454813\
Mark Gameng A20419026\
Shenlong Shen A20437413

### Program Execution
The only libraries required are **numpy** and **pandas**. To install these libraries do `pip install numpy` and `pip install pandas`

To run the program, simply type do `python probing.py` and it will start matching the probe points to a link and then deriving and evaluating the slopes.
Make sure to have *Partition6467LinkData.csv* and *Partition6467ProbePoints.csv* in your current working directory. The program will also output 
*Partition6467MatchedPoints.csv* and *Partition6467Slopes.csv*.

**Matching Probes takes a long time to process so it is better to use the included Partition6467MatchedPoints.csv instead, which has the probes matched already.**
**To do this, comment line 166 in probing.py. This will use the MatchedPoints csv file and calculate the slopes and finds the error from derived and surveyed slopes.**