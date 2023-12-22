ABOUT
==========

This IR system was created for a university course on Information Retrieval; it is coded in Python and runs in the command line. An inverted index is initially used to create the postings and dictionary files, followed by running the IR system via the user interface (ui.py). An evaluation (eval.py) of the system is also included.


The IR system uses a tf-idf weighting scheme with the log of base 10 with the following formulas:

f = total count of the term's occurrence in that document

tf = log(f) + 1

term_df = total count of the term in all documents

N = 3204 total docs in collection
idf = log(N / term_df)

Before running any of eval.py, search.py, or ui.py, invert.py must be run to creating the terms and postings files.


invert.py
==========
Runs in the command line 

To create an inverted index enter the following command in the command line--the third argument must be stemOn to turn on stemming or stemOff to turn off stemming:

i.e. to enable stemming:

```console
> python invert.py 'cacm.tar' stemOn
```

To disable stemming:

```console
> python invert.py 'cacm.tar' stemOff
```

Two output files, <terms_dict.json> and <postings_dict.json> will be created. The inverted index is organized alphabetically by term. The index of the term in terms_dict.json corresponds to the index of its postings in postings_dict.json.


search.py
===========
Returns the top 20 documents based on cosine similarity score. Before selecting the top-k docs, a threshold of 2.75 is set, so only document vectors with term weights of that magnitude will be selected to perform the cosine similarity.

To run in the command line:

```console
>> python search.py <query> <Yes/No>
```

<query> should be put in double quotes. Entering <Yes> enables stemming, while <No> disables it.



ui.py
==========

The file is run in the command line as:

<code>>> python ui.py</code>

The user will first be prompted to enter a free-text query, and then asked to confirm if stemming should be enabled or disabled, after which the command line will display a ranked retrieval of all relevant documents. The user will be continually prompted for further queries and can enter 'ZZEND' at either prompt to exit the program.

Example output:

<img src="Screenshot 2023-11-05 204239.png">

eval.py
==========

!! Note: This program takes roughly 35 seconds to complete on a 13th Gen Intel(R) Core(TM) i5-1335U processor. I attempted to lower the original time taken of ~60 seconds by using a multiprocessing pool over the total number of available CPUs minus 4. !!

This program runs on the command line as:

<code>>>python eval.py <Yes/No></code>

Where entering one of <code>Yes</code> or <code>No</code> as a command line argument enables (<code>Yes</code>) or disables (<code>No</code>) stemming on the query

qrels.text and query.text are taken in as inputs and parsed. This program first passes each extracted query into search.py. The returned top 20 docs from search.py is then used to calculate the AP, MAP and the average R-precision values. The MAP is displayed on the command line along with the average R-precision scores for each query.

An example output:

```console
python.exe eval.py Yes
Running evaluations...
Mean Average Precision (MAP): 0.17850279993492535
R-Precision values:
Query 1, R-Precision: 0.4
Query 2, R-Precision: 1.0
Query 3, R-Precision: 0.16666666666666666
Query 4, R-Precision: 0.08333333333333333
Query 5, R-Precision: 0.25
Query 6, R-Precision: 1.0
Query 7, R-Precision: 0.21428571428571427
Query 8, R-Precision: 0.3333333333333333
Query 9, R-Precision: 0.4444444444444444
Query 10, R-Precision: 0.08571428571428572
Query 11, R-Precision: 0.05263157894736842
Query 12, R-Precision: 0.4
Query 13, R-Precision: 0.0
Query 14, R-Precision: 0.13636363636363635
Query 15, R-Precision: 0.4
Query 16, R-Precision: 0.17647058823529413
Query 17, R-Precision: 0.0625
Query 18, R-Precision: 0.18181818181818182
Query 19, R-Precision: 0.09090909090909091
Query 20, R-Precision: 0.6666666666666666
Query 21, R-Precision: 0.09090909090909091
Query 22, R-Precision: 0.17647058823529413
Query 23, R-Precision: 0.0
Query 24, R-Precision: 0.07692307692307693
Query 25, R-Precision: 0.0
Query 26, R-Precision: 0.06666666666666667
Query 27, R-Precision: 0.0
Query 28, R-Precision: 0.8
Query 29, R-Precision: 0.2631578947368421
Query 30, R-Precision: 0.25
Query 31, R-Precision: 1.0
Query 32, R-Precision: 0.6666666666666666
Query 33, R-Precision: 1.0
Query 36, R-Precision: 0.2
Query 37, R-Precision: 0.16666666666666666
Query 38, R-Precision: 0.5
Query 39, R-Precision: 0.3333333333333333
Query 40, R-Precision: 0.4
Query 42, R-Precision: 0.0
Query 43, R-Precision: 0.07317073170731707
Query 44, R-Precision: 0.23529411764705882
Query 45, R-Precision: 0.23076923076923078
Query 48, R-Precision: 0.0
Query 49, R-Precision: 0.25
Query 57, R-Precision: 1.0
Query 58, R-Precision: 0.2
Query 59, R-Precision: 0.23255813953488372
Query 60, R-Precision: 0.2962962962962963
Query 61, R-Precision: 0.1935483870967742
Query 62, R-Precision: 0.125
Query 63, R-Precision: 0.08333333333333333
Query 64, R-Precision: 1.0
```