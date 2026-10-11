---
name: quiz-me
description: Practice quizzes for YOUR_NAME's 6 courses, built only from the text copies in _text. Use when YOUR_NAME says "quiz me", names a course plus a scope (e.g. "law course 2, thursday's quiz", "law course 1 sessions 18-22", "<case name>"), or asks for weak-spots practice. Modes: quick (5), standard (10), exam sim (timed, marks at the end), weak spots. Keeps a log per course in quizzes/<course>-log.md. Practice only; never touches a live graded Canvas quiz.
---

# Quiz me

Call: `/quiz-me <course> <scope> [quick | standard | exam sim | weak spots]`. If the mode is missing, ask. Every rule in CLAUDE.md applies. The ones that matter most here:

- Practice only. Never use this on a live graded Canvas quiz or test, never open its questions, never call any Canvas quiz tool (they are denied anyway). If YOUR_NAME asks to be helped through a live quiz, refuse and offer a practice quiz on the same scope.
- Read local files only: no Canvas calls, no browser, no web. Pearson/MyLab and other publisher platforms: never opened.
- Questions come only from the text copies in `_text/<Course>/...` (PDF, DOCX, PPTX, XLSX copies; `=== Page N ===` markers give the page). Never from memory, never invent law. If the material does not support a question, do not ask it.
- Sources: only official course materials from YOUR_NAME's teachers (Canvas files in the archive, the syllabus, announcements, and readings the teacher lists). No web searches, no other sites, no general knowledge to fill a gap, in questions, marking or explanations. If YOUR_NAME asks about something the materials do not cover, say "not covered in the provided materials".
- Reading summaries: `<Course>/_summaries/*.summary.md` are Claude's own summaries of course readings, written by `morning-digest`, each with file and page citations. Use them to find the scope, the key topics and the right pages faster. They are a map, not a source: before asking a question, open the cited page in `_text` and build the question, the answer and the citation from that page. If a summary and the text copy disagree, the text copy wins. Never write to `_summaries`.
- Past tests (optional): if YOUR_NAME saves their own marked tests as `past-tests/<Course>/*.md` (questions, options, their answer, the correct answer, feedback, notes on form and style), read the ones for the course before writing a quiz. Use them to copy the form (number of questions and options, question types, time limit, wording style), as open weak topics, and to re-ask a past question as revision labelled "(from past test, <date>)". New questions must still be supported by the text copies. This skill never opens Canvas and never writes to `past-tests/`.
- Write only to `quizzes/`. Read files with the Read tool. List and search files with the Glob and Grep tools, never with shell commands (`ls`, `find`, `grep`, `wc`). If Glob or Grep is not available in the session, take the file list from `<Course>/course-index.md` instead. The only shell command allowed is `mkdir -p quizzes` (if the folder is missing).
- Never delete or rewrite log entries; append and update only.

## 1. Find the scope

- **Named scope** (sessions 18-22, "<case name>", a topic): find the matching files under `_text/<Course>/` (use the Glob and Grep tools; read the course's `course-index.md` for the file map, and any matching summary in `<Course>/_summaries/` for the topics and pages).
- **Named quiz or exam** ("Thursday's quiz", "the midterm"): take the date from the Exams table in `<Course>/course-index.md`. Work out what it covers from the syllabus (text copy), the course's Announcements (text copies) and the course-index notes. Say where each part of the scope came from. If coverage is not stated anywhere, say so and propose a scope (e.g. "sessions 1-8, my assumption") instead of guessing silently.
- Tell YOUR_NAME the scope (files, sessions) and wait for a yes before the first question.

## 2. Check the text before quizzing

For every file in scope: check it has text and is complete (look for empty or very short pages, "Page N" gaps, scanned or garbled text, a text copy that is missing). Before the first question, warn YOUR_NAME about any file with missing or incomplete text, naming the pages, and about OCR text. Ask whether to continue without them. Never quiz from a missing or partial file without that warning. Mark any number or figure taken from an OCR page "(verify: OCR)".

## 3. Modes

- **Quick**: 5 questions. **Standard**: 10 questions.
- **Exam sim**: standard length unless YOUR_NAME says otherwise. Timed on the honour system: note the start time (your city; `date` is allowed) and say the time limit (ask YOUR_NAME, or suggest about 1.5 minutes per question). Ask all questions with no hints, no feedback and no marking until the end. YOUR_NAME tells you when finished; flag it if the stated time was over the limit. Then mark everything together: score, per-question marking, explanations and citations. Because there is no feedback in between, in exam sim give all the questions in one message (numbered) so YOUR_NAME can answer in one go.
- **Weak spots**: read `quizzes/<course>-log.md`. Questions only on topics logged as wrong and not yet cleared. If the log is missing or has no open topics, say so and offer a standard quiz.

## 4. Questions

Mix these types, in standard and quick modes one question at a time:

- **Multiple choice** (4 options, one correct; plausible wrong options).
- **Short answer.**
- **True/false with a reason**: YOUR_NAME must say true or false and why; mark both parts.
- **Fact pattern (law courses: Law Course 2, Law Course 1, Law Course 3)**: a short scenario built from facts and rules in the material, asking what the outcome is. For non-law courses (Course A, Course B, Course C) use short calculation or case questions instead.

Wait for YOUR_NAME's answer after each question. Do not give the answer or hints before it (exam sim: no hints at all).

### Mid-term / intermediate tests (optional)

When YOUR_NAME asks for a practice test for a course's real intermediate test, copy the form of the real one, as the teacher's announcement describes it (number of questions, number of options, marks, time limit, whether wrong answers lose marks, one attempt or several). Typical example: 20 multiple-choice questions, 5 options with 1 correct, 1 mark each, 20 minutes, no negative marking, all questions in one message, no hints, marking at the end.

- Spread the questions over all chapters or sessions in scope, as the teacher says everything in scope can be asked.
- If YOUR_NAME has saved past tests (see above), follow their "Form and style" notes: question length, mix of recall and mini-cases, how wrong options are written.
- Questions come only from the course materials (text copies, or your own notes on a textbook). Cite chapter and section. Do not ask about a chapter that has no notes or text yet; tell YOUR_NAME which are missing. Never fill a gap from general knowledge, and never open a publisher platform.

## 5. Marking

After each answer (exam sim: at the end):

- Say right, partly right or wrong, with a score (1 mark for objective questions; fact patterns out of 4).
- Explain briefly why.
- Cite the source: file path and page (e.g. `_text/Law Course 1/Own Materials/Session 10 - <topic>.pdf.txt, p. 4`). OCR figures marked "(verify: OCR)".
- **Fact patterns: mark on IRAC**: Issue, Rule, Application, Conclusion, 1 mark each. Say which parts were strong and which weak, and name the weakest part ("Your rule was right but the application skipped the facts about X").
- If YOUR_NAME's answer is wrong because the material is itself unclear or contradictory, say so rather than forcing a verdict.

At the end give the total score, the topics to revisit and, in IRAC terms, the part that was weakest across the fact patterns.

## 6. Log

Keep `quizzes/<course>-log.md`, course name lowercase with hyphens (`law-course-2`, `law-course-1`, `course-a`, `course-c`, `course-b`, `taxation`). If it does not exist, create it with a one-line title and an empty "Open weak topics" section. After each session, append a block:

```
## YYYY-MM-DD (your city) - <mode> - <scope>
Score: x/y
Wrong or weak: <topic> (<source file, page>); <topic> ...
IRAC weakest part: <Issue | Rule | Application | Conclusion | n/a>
```

Keep an "Open weak topics" list at the top of the file: add each topic YOUR_NAME got wrong with its date. A topic is cleared (move it to a "Cleared" list with the date) once YOUR_NAME gets it right in two quizzes in a row. Topics only, no copied question text from the course material. Update the log at the end of the session, or right away if YOUR_NAME stops early (note "stopped early").

## 7. Report

At the end: score, mode, scope, files used, any files warned about, and what was added to the log.
