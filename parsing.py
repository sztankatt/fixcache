"""Package to identify which line change is really a bug introduction."""
import re


def important_line(line):
    """Return True if line is important, in terms of bug introduction."""
    stripped_line = line.strip()
    if stripped_line.startswith('#') or stripped_line == '':
        return False

    return True


def _get_diff_deleted_line_counter(line):
        """Parse a diff line, to get the deleted lines in that diff.

        If the line parsed isn't a delete line, returns None.
        """
        regex1 = r'@@\s-(?P<start_line>\d+),(?P<line_num>\d+)'
        regex2 = r'@@\s-(?P<start_line>\d+),'
        regex3 = r'@@\s-(?P<start_line>\d+) +'
        pattern1 = re.compile(regex1)
        pattern2 = re.compile(regex2)
        pattern3 = re.compile(regex3)

        # check first for pattern with line number, then without it
        match1 = pattern1.match(line)
        match2 = pattern2.match(line)
        match3 = pattern3.match(line)
        ret_lines = (None, None)
        if match1 is not None:
            start_line = int(match1.group("start_line"))
            line_num = int(match1.group("line_num"))

            ret_lines = (start_line, line_num,)

        elif match2 is not None:
            start_line = int(match2.group("start_line"))

            ret_lines = (start_line, 0)

        elif match3 is not None:
            start_line = int(match3.group("start_line"))

            ret_lines = (start_line, 0)

        return ret_lines


def get_deleted_lines_from_diff(diff_lines):
    """Return deleted line numbers from a diff list."""
    if len(diff_lines) < 3:
        return []
    counter, _ = _get_diff_deleted_line_counter(diff_lines[2])
    if counter is None:
        return []
    counter -= 1
    line_list = []
    for line in diff_lines[3:]:
        if line.startswith('-'):
            line_list.append(counter)
            counter += 1
        elif line.startswith('+'):
            pass
        else:
            counter += 1

    return line_list


def is_fix_commit(message):
        """Return True if commit object is flagged as fixing."""
        m = message
        regexes = [
            r'defect(s)?',
            r'patch(ing|es|ed)?',
            r'bug(s|fix(es)?)?',
            r'(re)?fix(es|ed|ing|age\s?up(s)?)?',
            r'debug(ged)?',
            r'\#\d+',
            r'back\s?out',
            r'revert(ing|ed)?'
        ]
        for r in regexes:
            if re.search(r, m) is not None:
                return True

        return False
