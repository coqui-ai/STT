Contribution guidelines
=======================

Welcome to the 🐸STT project! We are excited to see your interest, and appreciate your support!

This repository is governed by the Contributor Covenant Code of Conduct. For more details, see the `CODE_OF_CONDUCT.md <CODE_OF_CONDUCT.md>`_.

How to Make a Good Pull Request
-------------------------------

Here's some guidelines on how to make a good PR to 🐸STT.

Bug-fix PR
^^^^^^^^^^

You've found a bug and you were able to squash it! Great job! Please write a short but clear commit message describing the bug, and how you fixed it. This makes review much easier. Also, please name your branch something related to the bug-fix.

New Feature PR
^^^^^^^^^^^^^^

You've made some core changes to 🐸STT, and you would like to share them back with the community -- great! First things first: if you're planning to add a feature (not just fix a bug or docs) let the 🐸STT team know ahead of time and get some feedback early. A quick check-in with the team can save time during code-review, and also ensure that your new feature fits into the project.

The 🐸STT codebase is made of many connected parts. There is Python code for training 🐸STT, core C++ code for running inference on trained models, and multiple language bindings to the C++ core so you can use 🐸STT in your favorite language.

Whenever you add a new feature to 🐸STT and what to contribute that feature back to the project, here are some things to keep in mind:

1. You've made changes to the core C++ code. Core changes can have downstream effects on all parts of the 🐸STT project, so keep that in mind. You should minimally also make necessary changes to the C client (i.e. **args.h** and **client.cc**). The bindings for Python, Java, and Javascript are SWIG generated, and in the best-case scenario you won't have to worry about them. However, if you've added a whole new feature, you may need to make custom tweaks to those bindings, because SWIG may not automagically work with your new feature, especially if you've exposed new arguments. The bindings for .NET and Swift are not generated automatically. It would be best if you also made the necessary manual changes to these bindings as well. It is best to communicate with the core 🐸STT team and come to an understanding of where you will likely need to work with the bindings. They can't predict all the bugs you will run into, but they will have a good idea of how to plan for some obvious challenges.
2. You've made changes to the Python code. Make sure you run a linter (described below).
3. Make sure your new feature doesn't regress the project. If you've added a significant feature or amount of code, you want to be sure your new feature doesn't create performance issues. For example, if you've made a change to the 🐸STT decoder, you should know that inference performance doesn't drop in terms of latency, accuracy, or memory usage. Unless you're proposing a new decoding algorithm, you probably don't have to worry about affecting accuracy. However, it's very possible you've affected latency or memory usage. You should run local performance tests to make sure no bugs have crept in. There are lots of tools to check latency and memory usage, and you should use what is most comfortable for you and gets the job done. If you're on Linux, you might find `perf <https://perf.wiki.kernel.org/index.php/Main_Page>`_ to be a useful tool. You can use sample WAV files for testing which are provided in the `STT/data/` directory.

Requesting review on your PR
----------------------------

Generally, a code owner will be notified of your pull request and will either review it or ask some other code owner for their review. If you'd like to proactively request review as you open the PR, see the the CODE_OWNERS.rst file which describes who's an appropriate reviewer depending on which parts of the code you're changing.


Code linting
------------

We use `pre-commit <https://pre-commit.com/>`_ to manage pre-commit hooks that take care of checking your changes for code style violations. Before committing changes, make sure you have the hook installed in your setup by running, in the virtual environment you use for running the code:

.. code-block:: bash

   cd STT
   python .pre-commit-2.11.1.pyz install

This will install a git pre-commit hook which will check your commits and let you know about any style violations that need fixing.
