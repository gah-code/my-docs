from __future__ import annotations
from flask import Blueprint, flash, redirect, render_template, request, url_for
from notalink.storage import NoteStore

ui = Blueprint("ui", __name__, template_folder="templates", static_folder="static")

@ui.get("/")
def home():
    store = NoteStore()
    notes = store.list_recent(limit=10)
    return render_template("home.html", notes=notes)

@ui.get("/notes/new")
def add_note_form():
    return render_template("add_note.html")

@ui.post("/notes/new")
def add_note_submit():
    payload = {
        "title": request.form.get("title") or None,
        "body": request.form.get("body") or "",
        "category": request.form.get("category") or "fleeting",
        "tags": [t.strip() for t in (request.form.get("tags") or "").split(",") if t.strip()],
        "source_url": request.form.get("source_url") or None,
        "source_kind": request.form.get("source_kind") or "manual",
    }
    store = NoteStore()
    note = store.create(payload)
    flash("Note saved.", "success")
    return redirect(url_for("ui.view_note", note_id=note.id))

@ui.get("/notes/<note_id>")
def view_note(note_id: str):
    store = NoteStore()
    note = store.get(note_id)
    if not note:
        flash("Note not found.", "error")
        return redirect(url_for("ui.home"))
    return render_template("view_note.html", note=note)
