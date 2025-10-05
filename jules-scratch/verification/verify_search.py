from playwright.sync_api import sync_playwright, expect
import time

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Go to the landing page and open the login modal
    page.goto("http://localhost:3000/landing")
    page.get_by_role("button", name="Login").first.click()

    # Wait for the modal to appear and fill in the login credentials
    login_modal = page.get_by_role("dialog", name="Login")
    expect(login_modal).to_be_visible()
    login_modal.get_by_label("User Name").fill("user1")
    login_modal.get_by_label("Password").fill("password")

    # Click the login button inside the modal
    login_modal.get_by_role("button", name="Login").click()

    # Wait for a moment to see if an error message appears
    time.sleep(2)

    # Take a screenshot to debug the login state
    page.screenshot(path="jules-scratch/verification/login_attempt.png")

    # Wait for navigation to the dashboard
    expect(page).to_have_url("http://localhost:3000/dashboard", timeout=10000)

    # Now, let's create a quiz so we can search for it
    page.get_by_text("Add Quiz").click()

    # Fill in the quiz details in the "Add New Quiz" modal
    add_quiz_modal = page.get_by_role("dialog", name="Add New Quiz")
    expect(add_quiz_modal).to_be_visible()

    add_quiz_modal.get_by_label("Quiz Name").fill("My Test Quiz for Search")
    add_quiz_modal.get_by_placeholder("Enter question body").fill("What is 1 + 1?")
    add_quiz_modal.get_by_placeholder("Enter answer 1").fill("1")
    add_quiz_modal.get_by_placeholder("Enter answer 2").fill("2")
    add_quiz_modal.get_by_placeholder("Enter answer 3").fill("3")
    add_quiz_modal.get_by_placeholder("Enter answer 4").fill("4")
    add_quiz_modal.get_by_label("Correct Answer").select_option("2")

    add_quiz_modal.get_by_role("button", name="Submit Quiz").click()

    # The modal should close, and we should be on the dashboard.
    # The quiz list should refresh. Let's wait for the new quiz to appear.
    expect(page.get_by_text("My Test Quiz for Search")).to_be_visible()

    # Now search for the quiz
    search_input = page.get_by_placeholder("Search quizzes...")
    expect(search_input).to_be_visible()
    search_input.fill("My Test Quiz")

    # Wait for the search results to appear
    expect(page.get_by_text("My Test Quiz for Search")).to_be_visible()

    # Take a screenshot
    page.screenshot(path="jules-scratch/verification/verification.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)