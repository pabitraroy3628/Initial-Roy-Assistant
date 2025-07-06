<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Ask Roy</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background: linear-gradient(to right top, #dee9ff, #e4f0ff, #f5fbff);
      font-family: 'Segoe UI', sans-serif;
      min-height: 100vh;
    }
    .main-card {
      background: rgba(255, 255, 255, 0.7);
      border-radius: 25px;
      padding: 40px;
      backdrop-filter: blur(12px);
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
      transition: all 0.3s ease;
    }
    .main-card:hover {
      transform: scale(1.01);
    }
    .hero-header {
      text-align: center;
      margin-bottom: 30px;
    }
    .hero-header h1 {
      font-weight: 700;
      font-size: 3rem;
    }
    .hero-header p {
      font-size: 1.15rem;
      color: #333;
    }
    .status-line {
      text-align: center;
      margin-bottom: 20px;
      font-weight: 500;
    }
    .status-line .available {
      color: green;
    }
    .status-line .away {
      color: red;
    }
    .suggestions {
      font-size: 0.95rem;
      margin-top: 20px;
      margin-bottom: 20px;
      color: #777;
      text-align: center;
    }
    .fade-in {
      animation: fadeIn 0.6s ease-in-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .roy-avatar {
      border-radius: 50%;
      border: 2px solid #ddd;
    }
  </style>
</head>
<body>

<div class="container py-5">
 <div class="hero-header">
  <h1>AskRoy</h1>
  <p class="text-muted mb-1">Roy’s Personal Assistant. I can help when Roy is unavailable. Ask me anything!</p>

  {% if status_message %}
  <p class="fw-semibold {% if 'available' in status_message %}text-success{% elif 'lunch' in status_message %}text-warning{% else %}text-danger{% endif %}">
    {{ status_message }}
  </p>
{% endif %}


  <div class="row justify-content-center">
    <div class="col-lg-8">
      <div class="main-card fade-in">
        <form method="POST">
          <div class="input-group mb-2">
            <input type="text" class="form-control form-control-lg" name="query" value="{{ query }}" placeholder="Ask me anything..." required autofocus>
            <button class="btn btn-primary btn-lg" type="submit">Ask Roy</button>
          </div>

          <div class="suggestions">
            🔍 Try: <em>Where is Roy?</em>, <em>Next holiday</em>, <em>Offers for Amazon card</em>, <em>Who is your manager?</em>
          </div>

          {% if offers %}
          <div class="card mt-4 shadow-sm fade-in">
            <div class="card-body d-flex align-items-start">
              {% if source == "roy" %}
                <img src="https://api.dicebear.com/7.x/thumbs/svg?seed=Roy" alt="Roy" width="48" height="48" class="me-3 roy-avatar">
              {% endif %}
              <div>
                <p style="white-space: pre-wrap;">{{ offers }}</p>
                {% if source == "roy" %}
                  <div class="badge bg-primary mt-3">Answered by Roy</div>
                {% elif source == "web" %}
                  <div class="badge bg-success mt-3">Answered from Web</div>
                {% endif %}
              </div>
            </div>
          </div>

          {% endif %}
        </form>
      </div>
    </div>
  </div>
</div>

</body>
</html>
