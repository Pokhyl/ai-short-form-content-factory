import unittest
from pathlib import Path


HTML = (Path(__file__).parents[2] / "factory_next" / "studio_web" / "index.html").read_text()


class StudioBatchUITests(unittest.TestCase):
    def test_topics_are_entered_one_per_line_with_per_topic_limit(self):
        self.assertIn('id="topic" required', HTML)
        self.assertIn("одна тема на строку", HTML)
        self.assertIn("topic.length>300", HTML)
        self.assertNotIn('id="topic" maxlength="300"', HTML)

    def test_each_topic_uses_the_existing_api_sequentially(self):
        self.assertIn(r"split(/\r?\n/)", HTML)
        self.assertIn("for(const [index,topic] of topics.entries())", HTML)
        loop = HTML.split("for(const [index,topic] of topics.entries())", 1)[1].split("}catch(e){", 1)[0]
        self.assertIn('await request(API,{method:"POST"', loop)
        self.assertIn("await loadJobHistory()", loop)
        self.assertNotIn("Promise.all", loop)

    def test_partial_acceptance_displays_persisted_job_ids(self):
        self.assertIn('" Принято заданий: "', HTML)
        self.assertIn('accepted.map(item=>item.id).join(", ")', HTML)
        self.assertIn('get("message").textContent=(e.message||"Ошибка соединения")+partial', HTML)


if __name__ == "__main__":
    unittest.main()
