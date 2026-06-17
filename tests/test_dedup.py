import pytest
from smolrag.dedup import dedup
from smolrag.types import CodeSnippet

def code_lines_generator(start_line, end_line):
    """generates dummy lines of code. example: (1, 4) returns "line1\nline2\nline3\nline4" """
    return "\n".join(["line" + str(x) for x in range(start_line, end_line)])


@pytest.mark.parametrize("snippets,expected", [
    pytest.param(
        [
            CodeSnippet(code=code_lines_generator(0, 5), path="f1", start_line=0, end_line=5),
            CodeSnippet(code=code_lines_generator(0, 5), path="f2", start_line=0, end_line=5),
        ],
        [
            CodeSnippet(code=code_lines_generator(0, 5), path="f1", start_line=0, end_line=5),
            CodeSnippet(code=code_lines_generator(0, 5), path="f2", start_line=0, end_line=5),
        ],
        id="different-files",
    ),
    pytest.param(
        [
            CodeSnippet(code=code_lines_generator(0, 5), path="f2", start_line=0, end_line=5),
            CodeSnippet(code=code_lines_generator(0, 5), path="f1", start_line=0, end_line=5),
        ],
        [
            CodeSnippet(code=code_lines_generator(0, 5), path="f2", start_line=0, end_line=5),
            CodeSnippet(code=code_lines_generator(0, 5), path="f1", start_line=0, end_line=5),
        ],
        id="file-order",
    ),
    pytest.param(
        [
            CodeSnippet(code=code_lines_generator(0, 3), path="f", start_line=0, end_line=3),
            CodeSnippet(code=code_lines_generator(2, 5), path="f", start_line=2, end_line=5),
        ],
        [CodeSnippet(code=code_lines_generator(0, 5), path="f", start_line=0, end_line=5)],
        id="overlapping-multiline",
    ),
    pytest.param(
        [
            CodeSnippet(code=code_lines_generator(0, 2), path="f", start_line=0, end_line=2),
            CodeSnippet(code=code_lines_generator(3, 5), path="f", start_line=3, end_line=5),
        ],
        [
            CodeSnippet(code=code_lines_generator(0, 2), path="f", start_line=0, end_line=2),
            CodeSnippet(code=code_lines_generator(3, 5), path="f", start_line=3, end_line=5),
        ],
        id="adjacent-not-merged",
    ),
    pytest.param(
        [
            CodeSnippet(code=code_lines_generator(0, 1), path="f", start_line=0, end_line=1),
            CodeSnippet(code=code_lines_generator(5, 6), path="f", start_line=5, end_line=6),
        ],
        [
            CodeSnippet(code=code_lines_generator(0, 1), path="f", start_line=0, end_line=1),
            CodeSnippet(code=code_lines_generator(5, 6), path="f", start_line=5, end_line=6),
        ],
        id="non-overlapping",
    ),
    pytest.param(
        [
            CodeSnippet(code=code_lines_generator(0, 10), path="f1", start_line=0, end_line=10),
            CodeSnippet(code=code_lines_generator(3, 5), path="f1", start_line=3, end_line=5),
        ],
        [CodeSnippet(code=code_lines_generator(0, 10), path="f1", start_line=0, end_line=10)],
        id="overlap-fully-contained",
    ),
    pytest.param(
        [
            CodeSnippet(code=code_lines_generator(0, 5), path="f", start_line=0, end_line=5),
            CodeSnippet(code=code_lines_generator(3, 8), path="f", start_line=3, end_line=8),
        ],
        [CodeSnippet(code=code_lines_generator(0, 8), path="f", start_line=0, end_line=8)],
        id="overlap-single-line",
    ),
    pytest.param(
        [
            CodeSnippet(code=code_lines_generator(0, 3), path="f", start_line=0, end_line=3),
            CodeSnippet(code=code_lines_generator(2, 6), path="f", start_line=2, end_line=6),
            CodeSnippet(code=code_lines_generator(5, 9), path="f", start_line=5, end_line=9),
        ],
        [CodeSnippet(code=code_lines_generator(0, 9), path="f", start_line=0, end_line=9)],
        id="overlap-chain",
    ),
    pytest.param(
        [
            CodeSnippet(code=code_lines_generator(0, 3), path="f", start_line=0, end_line=3),
            CodeSnippet(code=code_lines_generator(2, 6), path="f", start_line=2, end_line=6),
            CodeSnippet(code=code_lines_generator(10, 15), path="f", start_line=10, end_line=15),
        ],
        [
            CodeSnippet(code=code_lines_generator(0, 6), path="f", start_line=0, end_line=6),
            CodeSnippet(code=code_lines_generator(10, 15), path="f", start_line=10, end_line=15),
        ],
        id="overlap-mixed",
    ),
])
def test_dedup(snippets, expected):
    assert dedup(snippets) == expected
