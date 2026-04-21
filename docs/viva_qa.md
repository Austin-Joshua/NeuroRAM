# NeuroRAM Viva Questions and Answers

1. **Q:** What is NeuroRAM?  
   **A:** It is an intelligent predictive memory optimization system that monitors, predicts, analyzes, and recommends actions for RAM management.

2. **Q:** Which OS concept is central to NeuroRAM?  
   **A:** Virtual memory management, including RAM utilization, swap behavior, and process memory allocation.

3. **Q:** Why use `psutil`?  
   **A:** It provides safe, cross-platform access to process and system-level metrics such as RAM, CPU, and memory maps.

4. **Q:** Why is historical storage required?  
   **A:** ML models need historical sequences; trend and anomaly analysis also depend on persisted time-series data.

5. **Q:** Why was SQLite chosen?  
   **A:** It is lightweight, serverless, easy to integrate, and sufficient for single-node academic deployments.

6. **Q:** What are the core database tables?  
   **A:** `system_metrics`, `process_metrics`, `predictions`, and `alerts`.

7. **Q:** How is schema normalization applied?  
   **A:** System-level and process-level metrics are separated into dedicated tables to avoid redundancy.

8. **Q:** Which ML model is default and why?  
   **A:** `RandomForestRegressor` due to robust tabular performance and low tuning overhead.

9. **Q:** What is the target variable in prediction?  
   **A:** The next time-step RAM percentage (`target_next_ram`).

10. **Q:** Which features are used for prediction?  
    **A:** CPU percent, swap percent, available memory, time features, RAM lags, and rolling mean.

11. **Q:** Why include lag features?  
    **A:** They capture temporal dependency in RAM usage patterns.

12. **Q:** When do we use LSTM?  
    **A:** Optionally, when TensorFlow is available and sufficient data exists for sequential training.

13. **Q:** How is model quality evaluated?  
    **A:** Using MAE, RMSE, and R² on test data.

14. **Q:** What is memory leak heuristic in NeuroRAM?  
    **A:** Detection of sustained monotonic RAM growth above a configurable threshold window.

15. **Q:** What are risk classes?  
    **A:** `NORMAL`, `WARNING`, `CRITICAL`, `EMERGENCY`.

16. **Q:** How is risk determined?  
    **A:** By RAM threshold crossings and leak indicator escalation.

17. **Q:** What is the stability index?  
    **A:** A 0-100 health score combining RAM, CPU, swap, and risk penalties.

18. **Q:** Why is a single score useful?  
    **A:** It improves quick system-state interpretation in operational dashboards.

19. **Q:** Which DAA technique is used for ranking?  
    **A:** Sorting based on priority score; time complexity is O(n log n).

20. **Q:** What is the greedy strategy here?  
    **A:** Select top-k highest-priority processes for immediate optimization recommendations.

21. **Q:** What is priority score formula?  
    **A:** `0.7 * rss_mb + 0.3 * cpu_percent`.

22. **Q:** Why weight memory more than CPU?  
    **A:** The primary objective is RAM pressure mitigation, so RSS impact is emphasized.

23. **Q:** How does UI support decision-making?  
    **A:** With color-coded metrics, live charts, process table, and alert/recommendation panels.

24. **Q:** Why Streamlit for UI?  
    **A:** It enables fast, interactive data apps with minimal front-end overhead.

25. **Q:** Is the system safe?  
    **A:** Yes, it is non-destructive and does not kill processes automatically.

26. **Q:** How does NeuroRAM map to OS syllabus?  
    **A:** It demonstrates process management, memory utilization, swap, and resource allocation concepts.

27. **Q:** How does NeuroRAM map to DBMS syllabus?  
    **A:** It applies relational schema design, CRUD, persistence, and query functions.

28. **Q:** How does NeuroRAM map to ML syllabus?  
    **A:** It covers feature engineering, model training/testing, inference, and model persistence.

29. **Q:** How does NeuroRAM map to DAA syllabus?  
    **A:** It includes sorting-based ranking, greedy optimization, and complexity analysis.

30. **Q:** What are key future improvements?  
    **A:** Online learning, distributed collectors, richer anomaly models, and cloud-native integration.
