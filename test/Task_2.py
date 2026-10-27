
import uuid
from playwright.sync_api import sync_playwright, expect

BASE_URL = "https://parabank.parasoft.com/parabank/index.htm"


def test_parabank_end_to_end():
    username = "qa_" + uuid.uuid4().hex[:10]
    password = "Demo@12345"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(15000)

        try:
            # 1. Open ParaBank and register a new account
            print("Step 1: Opening ParaBank...")
            page.goto(BASE_URL, wait_until="domcontentloaded")

            page.get_by_role("link", name="Register").click()

            page.locator('[name="customer.firstName"]').fill("Test")
            page.locator('[name="customer.lastName"]').fill("User")
            page.locator('[name="customer.address.street"]').fill(
                "123 Demo Street"
            )
            page.locator('[name="customer.address.city"]').fill("Test City")
            page.locator('[name="customer.address.state"]').fill("CA")
            page.locator('[name="customer.address.zipCode"]').fill("90001")
            page.locator('[name="customer.phoneNumber"]').fill("5551234567")

            ssn = str(
                100000000 + int(uuid.uuid4().hex[:8], 16) % 900000000
            )
            page.locator('[name="customer.ssn"]').fill(ssn)
            page.locator('[name="customer.username"]').fill(username)
            page.locator('[name="customer.password"]').fill(password)
            page.locator('[name="repeatedPassword"]').fill(password)

            page.get_by_role("button", name="Register").click()

            expect(
                page.get_by_text(
                    "Your account was created successfully",
                    exact=False
                )
            ).to_be_visible(timeout=20000)

            print("Registration successful:", username)

            # 2. Open Accounts Overview and verify its content
            print("Step 2: Opening Accounts Overview...")
            page.get_by_role("link", name="Accounts Overview").click()

            expect(
                page.get_by_role("heading", name="Accounts Overview")
            ).to_be_visible(timeout=15000)

            # Use the account table if it exists; otherwise report the page content.
            account_table = page.locator("#accountTable")
            expect(account_table).to_be_visible(timeout=15000)

            account_link = account_table.locator("a").first
            expect(account_link).to_be_visible()

            account_number = account_link.inner_text().strip()
            print("Account number:", account_number)
            print("STEP 1 PASSED: Accounts Overview displayed.")

            # 3. Open account details
            print("Step 3: Opening account details...")
            account_link.click()

            expect(page.locator("#accountId")).to_be_visible()
            expect(page.locator("#accountType")).to_be_visible()
            expect(page.locator("#balance")).to_be_visible()

            print("Account ID:", page.locator("#accountId").inner_text())
            print("Account type:", page.locator("#accountType").inner_text())
            print("Balance:", page.locator("#balance").inner_text())
            print("STEP 2 PASSED: Account details displayed.")

            # 4. Transfer funds using available account dropdown options
            print("Step 4: Opening Transfer Funds...")
            page.get_by_role("link", name="Transfer Funds").click()

            expect(page.locator("#amount")).to_be_visible()

            from_dropdown = page.locator("#fromAccountId")
            to_dropdown = page.locator("#toAccountId")

            from_dropdown.wait_for(state="visible")
            to_dropdown.wait_for(state="visible")

            source_options = from_dropdown.locator("option").all()
            destination_options = to_dropdown.locator("option").all()

            source_id = next(
                (
                    option.get_attribute("value")
                    for option in source_options
                    if option.get_attribute("value")
                ),
                None
            )

            destination_id = next(
                (
                    option.get_attribute("value")
                    for option in destination_options
                    if option.get_attribute("value")
                    and option.get_attribute("value") != source_id
                ),
                None
            )

            if source_id and destination_id:
                from_dropdown.select_option(source_id)
                to_dropdown.select_option(destination_id)

                page.locator("#amount").fill("1.00")
                page.get_by_role("button", name="Transfer").click()

                result = page.locator("#showResult")
                expect(result).to_be_visible(timeout=15000)

                print("Transfer result:", result.inner_text())

                # Search for the transaction
                print("Searching for the transaction...")
                page.get_by_role("link", name="Find Transactions").click()

                expect(page.locator("#accountId")).to_be_visible()
                page.locator("#accountId").select_option(source_id)

                amount_field = page.locator("#amount")
                if amount_field.is_visible():
                    amount_field.fill("1.00")

                page.get_by_role(
                    "button", name="Find Transactions"
                ).click()

                page.wait_for_load_state("domcontentloaded")
                print(
                    "Transaction page content:",
                    page.locator("body").inner_text()[:2000]
                )
            else:
                print(
                    "TRANSFER SKIPPED: Two distinct accounts are not available."
                )

            # 5. Hover test
            print("Step 5: Testing hover...")
            solutions = page.get_by_role("link", name="Solutions")

            if solutions.count() > 0 and solutions.is_visible():
                solutions.hover()
                print("Hover action performed on Solutions.")
            else:
                print("Solutions link is not available for hover.")

            # 6. Check hidden and collapsed elements
            print("Step 6: Checking hidden/collapsed elements...")

            hidden_elements = page.locator(
                'input[type="hidden"], [aria-hidden="true"]'
            )
            print("Hidden elements found:", hidden_elements.count())

            expand_controls = page.locator(
                'button[aria-expanded="false"], '
                '[role="button"][aria-expanded="false"]'
            )

            expanded = False
            for index in range(expand_controls.count()):
                control = expand_controls.nth(index)
                if control.is_visible() and control.is_enabled():
                    control.click()
                    expanded = True
                    print("Expanded a visible collapsed control.")
                    break

            if not expanded:
                print("No visible collapsed control was available.")

            # 7. Right-click and double-click on a safe navigation link
            print("Step 7: Testing right-click and double-click...")
            overview_link = page.get_by_role(
                "link", name="Accounts Overview"
            )

            if overview_link.count() > 0 and overview_link.is_visible():
                overview_link.click(button="right")
                print("Right-click tested.")

                overview_link.dblclick()
                print("Double-click tested.")

            # 8. Logout and verify the login page
            print("Step 8: Logging out...")
            logout = page.get_by_role("link", name="Log Out")
            expect(logout).to_be_visible(timeout=15000)
            logout.click()

            expect(
                page.locator('input[name="username"]')
            ).to_be_visible(timeout=15000)

            expect(
                page.locator('input[name="password"]')
            ).to_be_visible(timeout=15000)

            print("STEP 8 PASSED: Logout verified.")

        finally:
            browser.close()
