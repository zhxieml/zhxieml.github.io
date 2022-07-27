---
layout: publication
---

<ul>
  {% for publication in site.publications %}
    <li>
      <h2>{{ publication.title }}</h2>
      <h3>{{ publication.authors }}</h3>
      <p>{{ publication.content | markdownify }}</p>
    </li>
  {% endfor %}
</ul>