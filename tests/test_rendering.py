from app.services.rendering import render_recommendation


def test_rendering_escapes_user_content():
    text = render_recommendation('<b>bad</b>', 'A&B', '<script>', 'HEADER', 'FOOTER')
    assert '&lt;b&gt;bad&lt;/b&gt;' in text
    assert 'A&amp;B' in text
    assert '&lt;script&gt;' in text
