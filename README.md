# Qu - queueing language 

Qu is a non-Turing-complete programming language designed to queue objects on a reveal-js presentation slide. For example, if an user wants to display “image1” first, then the text “text1”, they can express it as the following code:
    “<1-> image1
    <2-> text1”
which, after rendering to the presentation slide, would behave as expected.

Qu aims to provide the great control that Latex Beamer and Python Manim has, without the extra copy-paste or a steep learning curve. The language is simple, and it serves to do one thing only: queue objects so that they appear in the desired order. 

The programming language has 2 main parts: the language design and a compiler. The design of the language is determined by the context-free grammar that specifies the production rules. The first part of the compiler takes in source code written in Qu, creates a matrix that shows the status (visible = 1, invisible = 0) of each object in each slide. This matrix clearly expresses all the objects and its visibility on each slide, making the process of automating slide making
easier.

Most of the necessary theoretical knowledge for this project is from from CS302 - Theory of Computing class at Fulbright. This project provides practical experiences in language design and compiler building. My goal is to get hands-on experience at designing domain-specific languages for a specific software.


**Note**: Qu is developed as part of an internal tool, lead by a professor at Fulbright Univrsity Vietnam. As of now (January 2024), I am no longer a part of this big project. 

The original repository for this project can be found at: https://github.com/ducquando/express-server, which contains only the parser I wrote but no grammar design file. I uploaded all parts of my work to this repository to archive both the language design and the parser implementation. 

