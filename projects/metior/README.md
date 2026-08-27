> **Vendored snapshot.** From the ASE 2021 research artifact for "Performance Testing for Cloud Computing with
> Dependent Data Bootstrapping" (He et al.). Code lives in [`src/`](src/); `LICENSE.md` (BSD-2.0), `STATUS.md`,
> and `INSTALL.md` kept at the folder root. The paper PDF, `INSTALL.pdf`, the `Prep/` duplicates, and the empty
> `AWS/` and `Chameleon/` data directories were removed.

This artifact is used to apply for &quot;Available&quot; badge for the accepted paper &quot;Performance Testing for Cloud Computing with Dependent Data Bootstrapping&quot; at ASE 2021 conference.

##### Artifact Description
This artifact contain code and data used to generate the data in Evaluation section (Section 4), which are the evaluation results of Metior. More specifically, the results obtained from Metior in Figure 7, Figure 8 and Figure 9. For usage, please refer to INSTALL.pdf

##### Files
Following supporting materials are included in the package:

1. &quot;ase2021-paper1.pdf&quot;, the PDF file of our accepted paper.
2. &quot;README.md&quot; is this file.
3. &quot;STATUS.md&quot; stats we are applying for &quot;Available&quot;, and why we are applying for them.
4. &quot;LICENSE.md&quot; contains the description of the distribution rights.
5. &quot;INSTALL.MD&quot; is the simplified instruction for executing our code.
6. &quot;INSTALL.pdf&quot; is the detailed instruction for executing our code.
7. &quot;MetiorArtifacts.py&quot; is the main script of our Metior methodology.
8. &quot;load_data.py&quot; is the script for load test data.
9. &quot;AWS/&quot; and &quot;Chameleon/&quot; directory contains the experiment data collected from our experiment.



##### Implementation Information
1. The main Metior logic is implemented in &quot;MetiorArtifacts.py&quot; in function &quot;Metior&quot;
2. The function for Dependent data bootstrapping is implemented in &quot;MetiorArtifacts.py&quot; in function &quot;block_bootstrap&quot; 

