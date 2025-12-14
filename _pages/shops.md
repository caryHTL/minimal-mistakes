---
layout: archive
title: 在地水電行
description: 收錄在地水電、五金行與相關店家的獨立頁面索引。
permalink: /shops/
classes: wide
---

{%- assign shops = site.data.shops -%}
{%- if shops and shops.size > 0 -%}
<div class="grid__wrapper">
  {%- for shop in shops -%}
  <article class="archive__item" itemscope itemtype="https://schema.org/LocalBusiness">
    <h2 class="archive__item-title" itemprop="name">
      <a href="/shops/{{ shop.slug }}/">{{ shop.name }}</a>
    </h2>
    {%- if shop.category -%}
    <p class="archive__item-excerpt" itemprop="priceRange">{{ shop.category }}</p>
    {%- endif -%}
    {%- if shop.address -%}
    <p class="archive__item-excerpt" itemprop="address">{{ shop.address }}</p>
    {%- endif -%}
    {%- if shop.rating -%}
    <p class="archive__item-excerpt">⭐ {{ shop.rating }}{% if shop.review_count %}（{{ shop.review_count }} 則評論）{% endif %}</p>
    {%- endif -%}
  </article>
  {%- endfor -%}
</div>
{%- else -%}
<p>目前沒有店家資料。</p>
{%- endif -%}
