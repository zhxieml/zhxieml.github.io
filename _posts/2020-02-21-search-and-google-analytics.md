---
layout: post
title: <改造> 添加搜索和流量统计
cover: Google-Analytics.jpg
date:   2020-02-21 17:00:00
category: blog
tag: tech
---

> Blog页面看着有点单调，闲来无事加上搜索功能和流量统计，感谢优秀项目[Simple Jekyll Search](https://github.com/christian-fei/Simple-Jekyll-Search)和[Google Analytics](https://analytics.google.com/)。

## Simple Jekyll Search
一个简单易用的轻量Blog搜索功能，不多不少地满足了我的需求。开源万岁！

整个配置过程就两步：

### 一、添加search.json
放在`根目录`下，用于明确搜索数据源。

```json
---
layout: null
---
[
  {% for post in site.posts %}
    {
      "title"    : "{{ post.title | escape }}",
      "category" : "{{ post.category }}",
      "tags"     : "{{ post.tags | join: ', ' }}",
      "url"      : "{{ site.baseurl }}{{ post.url }}",
      "date"     : "{{ post.date }}"
    } {% unless forloop.last %},{% endunless %}
  {%
   endfor %}
]
```

**Simple Jekyll Search**能够做到如此简单的精妙之处就在于此。通过添加“空的”YAML头文件，Jekyll将自动通过[Liquid](https://github.com/Shopify/liquid)生成数据，并直接交由JS处理。

### 二、在layout中放置搜索框

这一步关键在于搜索框的参数配置：

```html
<script>
    window.simpleJekyllSearch = new SimpleJekyllSearch({
		searchInput: document.getElementById('search-input'),
        resultsContainer: document.getElementById('results-container'),
        json: '{{ site.baseurl }}/search.json',
        searchResultTemplate: '<li><a href="{{ site.url }}{url}" title="{date}">{title}</a></li>',
        noResultsText: '无结果',
        limit: 10,
        fuzzy: false,
        exclude: ['Welcome']
	})
</script>
```

根据[Wiki](https://github.com/christian-fei/Simple-Jekyll-Search/wiki#options)，按照参数逐一设置。

## Google Analytics

在[官网](https://analytics.google.com/)注册一下拿到个**Tracking ID**，把其添加到`_config.yml`中，然后在`_includes`文件夹里创建相应的内容：

```html
<script>
	(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
	(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');
  
	ga('create', '{{ site.google_analytics }}', 'auto');
	ga('send', 'pageview');
  
</script>
```

最后在相应位置include即可。