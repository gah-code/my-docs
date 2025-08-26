from notalink.storage import NoteStore
def test_note_store_smoke():
    store = NoteStore()
    note = store.create({"body": "hello world.", "category": "fleeting", "tags": ["smoke"]})
    assert note.id and store.get(note.id)
