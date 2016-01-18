import re
""" Package to identify which line change is really a bug introduction,
and which one does not affect the repository at all.
"""


def important_line(line):
    """returns True if line is important, in terms of bug introduction"""
    return True


def get_deletes(line):
        """parses a diff line, to get the deleted lines in that diff.
        If the line parsed isn't a delete line, returns None"""
        regex1 = r'@@\s-(?P<start_line>\d+),(?P<line_num>\d+)'
        regex2 = r'@@\s-(?P<start_line>\d+),'
        pattern1 = re.compile(regex1)
        pattern2 = re.compile(regex2)

        # check first for pattern with line number, then without it
        match1 = pattern1.match(line)
        match2 = pattern2.match(line)

        if match1 is not None:
            start_line = int(match1.group("start_line"))
            line_num = int(match1.group("line_num"))

            return (start_line, line_num,)

        if match2 is not None:
            start_line = match2.group("start_line")

            return (start_line, 0)

        return None


def is_fix_commit(message):
        """returns True if commit object is flagged as fixing"""
        m = message
        regex = r'[Ff][Ii][Xx]([Ee][Ss])*'
        if re.search(regex, m) is not None:
            return True
        else:
            return False
