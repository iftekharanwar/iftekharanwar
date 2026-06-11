#!/usr/bin/env python3
"""Tic-tac-toe played through GitHub issues. Humans are X, the bot is O."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "assets" / "game.json"
BOARD_SVG = ROOT / "assets" / "board.svg"
README = ROOT / "README.md"

BG, GRID, XCOL, OCOL, TXT = "#00000f", "#2d2d86", "#5ad4d4", "#d45ad4", "#eeeeff"
LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
ISSUE_URL = ("https://github.com/iftekharanwar/iftekharanwar/issues/new"
             "?title=ttt%7C{pos}&body=Just+press+%22Submit+new+issue%22+%E2%80%94+the+bot+answers+in+~30s.")


def load():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"board": [""] * 9, "stats": {"humans": 0, "bot": 0, "draws": 0}, "last": ""}


def winner(b):
    for a, c, d in LINES:
        if b[a] and b[a] == b[c] == b[d]:
            return b[a]
    return "draw" if all(b) else ""


def minimax(b, player):
    w = winner(b)
    if w == "O":
        return 1, None
    if w == "X":
        return -1, None
    if w == "draw":
        return 0, None
    best = (-2, None) if player == "O" else (2, None)
    for i in range(9):
        if not b[i]:
            b[i] = player
            score, _ = minimax(b, "X" if player == "O" else "O")
            b[i] = ""
            if player == "O" and score > best[0]:
                best = (score, i)
            if player == "X" and score < best[0]:
                best = (score, i)
    return best


def render_board(b, status):
    cells = []
    for i, v in enumerate(b):
        x, y = 40 + (i % 3) * 80, 50 + (i // 3) * 80
        if v == "X":
            cells.append(f'<g stroke="{XCOL}" stroke-width="7" stroke-linecap="round">'
                         f'<line x1="{x+18}" y1="{y+18}" x2="{x+62}" y2="{y+62}"/>'
                         f'<line x1="{x+62}" y1="{y+18}" x2="{x+18}" y2="{y+62}"/></g>')
        elif v == "O":
            cells.append(f'<circle cx="{x+40}" cy="{y+40}" r="24" stroke="{OCOL}" stroke-width="7" fill="none"/>')
        else:
            cells.append(f'<text x="{x+40}" y="{y+48}" text-anchor="middle" font-size="22" fill="#444466">{i+1}</text>')
    grid = "".join(
        f'<line x1="{40+i*80}" y1="50" x2="{40+i*80}" y2="290" stroke="{GRID}" stroke-width="3"/>'
        f'<line x1="40" y1="{50+i*80}" x2="280" y2="{50+i*80}" stroke="{GRID}" stroke-width="3"/>'
        for i in range(1, 3))
    BOARD_SVG.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 330" font-family="ui-monospace,Menlo,monospace">'
        f'<rect width="320" height="330" rx="12" fill="{BG}" stroke="{GRID}"/>'
        f'<text x="160" y="30" text-anchor="middle" font-size="14" fill="{TXT}">{status}</text>'
        f'{grid}{"".join(cells)}</svg>\n')


def render_readme(state, status):
    b = state["board"]
    s = state["stats"]
    free = [str(i + 1) for i in range(9) if not b[i]]
    links = " · ".join(f"[{p}]({ISSUE_URL.format(pos=p)})" for p in free) or "—"
    section = (
        "<!--TTT:START-->\n"
        '<img src="./assets/board.svg" width="300" alt="tic-tac-toe board"/>\n\n'
        f"**Your move:** {links}\n\n"
        f"`humans {s['humans']} · bot {s['bot']} · draws {s['draws']}`"
        f"{' · last player: **' + state['last'] + '**' if state['last'] else ''}\n"
        "<!--TTT:END-->")
    text = README.read_text()
    README.write_text(re.sub(r"<!--TTT:START-->.*?<!--TTT:END-->", section, text, flags=re.S))
    render_board(b, status)


def main():
    state = load()
    b = state["board"]
    msg = ""

    if len(sys.argv) >= 2 and sys.argv[1] == "init":
        render_readme(state, "you are X — pick a square")
        STATE.write_text(json.dumps(state))
        return

    if not sys.argv[1].isdigit():
        (ROOT / "comment.md").write_text("That title isn't a move I understand — use the links in the README.")
        return
    pos, player = int(sys.argv[1]) - 1, sys.argv[2]
    if not 0 <= pos <= 8 or b[pos] or winner(b):
        msg = f"Square {pos + 1} is taken or the game moved on. Check the board for the live state."
    else:
        b[pos] = "X"
        state["last"] = f"@{player}"
        w = winner(b)
        if not w:
            _, bot = minimax(b, "O")
            b[bot] = "O"
            w = winner(b)
        if w == "X":
            state["stats"]["humans"] += 1
            msg = f"@{player} beat the bot. New board is up."
            status = f"@{player} won — new game"
        elif w == "O":
            state["stats"]["bot"] += 1
            msg = f"Bot wins, @{player}. It plays perfect minimax, so a draw is the best anyone can get. New board is up."
            status = "bot won — new game"
        elif w == "draw":
            state["stats"]["draws"] += 1
            msg = f"Draw, @{player}. Against minimax that's the ceiling. New board is up."
            status = "draw — new game"
        else:
            msg = f"Move played, @{player}. The bot answered, your turn."
            status = "you are X — your move"
        if w:
            state["board"] = [""] * 9
        render_readme(state, status)

    STATE.write_text(json.dumps(state))
    (ROOT / "comment.md").write_text(msg)


if __name__ == "__main__":
    main()
