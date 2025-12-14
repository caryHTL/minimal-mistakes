{% assign shop = shop | default: page %}

{% if shop.image_url %}
![{{ shop.name | default: page.title }} 圖片]({{ shop.image_url }}){: .align-center }
{% endif %}

- **類型：** {{ shop.category | default: '—' }}
- **評分：** {% if shop.rating %}{{ shop.rating }}{% else %}—{% endif %} {% if shop.review_count %}(約 {{ shop.review_count }} 則評論){% endif %}
- **地址：** {{ shop.address | default: '—' }}
- **電話：** {{ shop.phone | default: '—' }}
- **營業狀態：** {{ shop.status | default: '—' }} {% if shop.hours_note %}{{ shop.hours_note }}{% endif %}

{% if shop.review_snippet %}
> {{ shop.review_snippet }}
{% endif %}

{% if shop.map_url %}
[在 Google Maps 開啟]({{ shop.map_url }}){: .btn .btn--primary }
{% endif %}
