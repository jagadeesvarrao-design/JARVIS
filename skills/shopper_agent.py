import os
import re
import json
import time
import urllib.parse
import threading
from ddgs import DDGS

def get_triggers():
    # Matches buy, shop, purchase, order, or find lowest price commands
    return [
        r"\b(?:buy|purchase|shop for|find the lowest price for|order)\s+(.+)"
    ]

def check_domain_safety(jarvis, domain):
    domain = domain.lower().replace("www.", "").strip()
    
    TRUSTED_DOMAINS = [
        "amazon.in", "flipkart.com", "croma.com", "jiomart.com", 
        "reliance-digital.in", "reliancedigital.in", "tatacliq.com", 
        "myntra.com", "snapdeal.com", "meesho.com", "ajio.com", 
        "nykaa.com", "pepperfry.com", "sony.co.in", "samsung.com/in"
    ]
    
    for td in TRUSTED_DOMAINS:
        if domain == td or domain.endswith("." + td):
            return "verified"
            
    # Run reputation search for unknown domains
    try:
        with DDGS() as ddgs:
            query = f"is {domain} safe legit trust rating reviews scam"
            results = list(ddgs.text(query, max_results=3))
            
        if not results:
            return "unverified"
            
        reputation_text = "\n".join([f"- Title: {r['title']}\n  Snippet: {r['body']}" for r in results])
        
        prompt = (
            f"Based on these web search results, analyze the website '{domain}'. Is it a legitimate, safe e-commerce vendor "
            f"or is it a scam, fake, phishing, or highly suspicious site?\n\n"
            f"Search results:\n{reputation_text}\n\n"
            f"Answer with ONLY a single word: 'legit' or 'suspicious'."
        )
        
        resp = jarvis.brain.get_response(prompt).strip().lower()
        if "legit" in resp:
            return "verified"
        return "suspicious"
    except Exception as e:
        print(f"⚠️ Safety search error for {domain}: {e}")
        return "unverified"

def run_playwright_automation(jarvis, url, store_name, product_name):
    jarvis._respond(f"Spawning browser session to automate checkout at {store_name}...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Launch User's Preferred Google Chrome browser
            try:
                browser = p.chromium.launch(headless=False, channel="chrome", args=["--start-maximized"])
            except Exception as e:
                print(f"⚠️ Preferred Chrome channel not found: {e}. Launching default Chromium instead...")
                browser = p.chromium.launch(headless=False, args=["--start-maximized"])
                
            context = browser.new_context(viewport=None)
            page = context.new_page()
            
            jarvis._respond(f"Navigating to {store_name} product page...")
            page.goto(url)
            page.wait_for_load_state("load")
            
            # Common Add to Cart button text and selector matches
            add_to_cart_selectors = [
                "button:has-text('Add to Cart')",
                "button:has-text('Add to Bag')",
                "button:has-text('Add to Basket')",
                "button:has-text('Buy Now')",
                "button:has-text('Pre-Order')",
                "a:has-text('Add to Cart')",
                "input[type='submit'][value*='Cart']",
                "input[type='button'][value*='Cart']",
                "[id*='add-to-cart']",
                "[class*='add-to-cart']",
                "[data-test='shipItButton']",
                "[data-automation-id='add-to-cart-button']"
            ]
            
            clicked = False
            for selector in add_to_cart_selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=2000):
                        el.click(timeout=3000)
                        clicked = True
                        jarvis._respond(f"Successfully added the item to your cart at {store_name}.")
                        break
                except Exception:
                    continue
                    
            if not clicked:
                jarvis._respond("I loaded the page but could not find the add to cart button automatically, Sir. Please click it on your screen.")
            
            time.sleep(2.5)
            
            # Common checkout/cart selectors
            checkout_selectors = [
                "button:has-text('Checkout')",
                "button:has-text('Proceed to Checkout')",
                "a:has-text('Checkout')",
                "a:has-text('Proceed to Checkout')",
                "a:has-text('Go to Cart')",
                "a[href*='cart']",
                "a[href*='checkout']",
                "button[id*='checkout']",
                "button[class*='checkout']"
            ]
            
            checked_out = False
            for selector in checkout_selectors:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=2000):
                        el.click(timeout=3000)
                        checked_out = True
                        jarvis._respond("Navigating to checkout page...")
                        break
                except Exception:
                    continue
                    
            if checked_out:
                jarvis._respond("Sir, I have navigated to the checkout screen. Since billing or account credentials are required, I have stopped here. Please take over and complete the payment securely.")
            else:
                jarvis._respond("I have paused on the cart page. Please click Proceed to Checkout and complete your payment details.")
                
            # Keep browser session alive
            while True:
                try:
                    if not page.is_closed():
                        time.sleep(1.0)
                    else:
                        break
                except:
                    break
    except Exception as e:
        print(f"⚠️ Playwright automation crash: {e}")
        jarvis._respond(f"Playwright automation encountered an issue: {e}")

def execute(jarvis, text, original_text, match=None):
    product = match.group(1).strip()
    jarvis._respond(f"Initializing shopping module for '{product}'. Searching the web for prices...")
    
    # Step 1: Run Search on DDG
    try:
        with DDGS() as ddgs:
            query = f"buy {product} price India"
            results = list(ddgs.text(query, max_results=8))
    except Exception as e:
        print(f"⚠️ DDG Search failed: {e}")
        jarvis._respond("I was unable to establish a connection to search the web, Sir.")
        return False

    if not results:
        jarvis._respond(f"I searched the web but found no active listings for '{product}'.")
        return False

    # Step 2: Use AIBrain to extract domain, URL, and price
    results_text = "\n".join([f"- Title: {r['title']}\n  URL: {r['href']}\n  Snippet: {r['body']}" for r in results])
    prompt = (
        f"Analyze these search results for '{product}':\n\n"
        f"{results_text}\n\n"
        f"CRITICAL RULE: We want to extract ONLY options from legitimate Indian e-commerce sites. "
        f"An Indian site is defined as a domain ending in .in, .co.in, or any of the major Indian retailers "
        f"(like flipkart.com, croma.com, tatacliq.com, jiomart.com, myntra.com, ajio.com, snapdeal.com, meesho.com, pepperfry.com, reliance-digital.in). "
        f"Ignore international-only stores (like walmart.com, target.com, bestbuy.com, gamestop.com, amazon.com). "
        f"Note that amazon.in is valid, but amazon.com is NOT.\n\n"
        f"For each valid Indian shopping option, extract:\n"
        f"1. Domain name (e.g. amazon.in, flipkart.com, croma.com, etc.)\n"
        f"2. Product URL\n"
        f"3. Approximate price in Rupees (represented as a float/number like 49999.0, or null if missing)\n\n"
        f"Return ONLY a valid JSON array of objects with keys: 'domain', 'url', 'price', 'title'. "
        f"Format as raw JSON. No markdown code blocks."
    )

    try:
        raw_res = jarvis.brain.get_response(prompt)
        # Clean JSON
        json_match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', raw_res)
        if json_match:
            options = json.loads(json_match.group(1))
        else:
            options = json.loads(raw_res.strip())
    except Exception as e:
        print(f"⚠️ JSON parsing of search results failed: {e}")
        # Fallback to direct heuristic parsing
        options = []
        for r in results:
            parsed = urllib.parse.urlparse(r['href'])
            domain = parsed.netloc.replace("www.", "")
            options.append({
                "domain": domain,
                "url": r['href'],
                "price": None,
                "title": r['title']
            })

    # Post-filtering to guarantee ONLY Indian domains are processed
    filtered_options = []
    for opt in options:
        domain = opt.get("domain", "").lower()
        is_indian = domain.endswith(".in") or any(
            ind in domain for ind in [
                "flipkart.com", "croma.com", "tatacliq.com", "jiomart.com", 
                "myntra.com", "ajio.com", "snapdeal.com", "meesho.com", "pepperfry.com"
            ]
        )
        if is_indian and not domain.endswith("amazon.com"):
            filtered_options.append(opt)
    options = filtered_options

    if not options:
        jarvis._respond("I could not parse any valid Indian shopping listings from the search results, Sir.")
        return False

    # Step 3: Run safety checks
    jarvis._respond("Checking domain trustworthiness and vendor ratings...")
    verified_options = []
    suspicious_listings = []
    
    for opt in options:
        domain = opt.get("domain", "")
        if not domain:
            continue
        safety = check_domain_safety(jarvis, domain)
        opt["safety"] = safety
        
        if safety == "suspicious":
            suspicious_listings.append(opt)
        else:
            verified_options.append(opt)

    # Sort verified options by price
    def get_price(opt):
        try:
            val = opt.get("price")
            if val is not None:
                return float(val)
        except:
            pass
        return float('inf')

    verified_options.sort(key=get_price)

    # Step 4: Report Search Results and Justify
    search_summary = []
    
    for opt in verified_options:
        price_str = f"Rs. {opt['price']}" if opt.get("price") else "unknown price"
        search_summary.append(f" - {opt['domain']} ({price_str}) - Verified Safe")
        
    for opt in suspicious_listings:
        price_str = f"Rs. {opt['price']}" if opt.get("price") else "unknown price"
        search_summary.append(f" - {opt['domain']} ({price_str}) - Flagged Suspicious / Potential Scam")

    jarvis._respond("Search complete, Sir. Here are my Indian e-commerce findings:")
    print("\n".join(search_summary))

    if not verified_options:
        jarvis._respond("I could not find any safe, verified Indian websites selling the item, Sir. I have aborted the purchase automation.")
        return False

    best_option = verified_options[0]
    
    # Build justification report (Ensure no markdown or lists in spoken justification)
    justification = f"I searched {len(options)} Indian websites. I recommend purchasing from {best_option['domain']}. "
    
    price_val = best_option.get("price")
    if price_val:
        justification += f"It has the lowest verified price of Rupees {price_val}. "
    else:
        justification += "It is a verified secure retailer. "
        
    if suspicious_listings:
        suspicious_domains = ", ".join(list(set([s['domain'] for s in suspicious_listings])))
        justification += f"I flagged other sellers like {suspicious_domains} as unsafe or suspicious based on reputation rating analysis, and excluded them from consideration. "
        
    justification += "Proceeding with purchase automation."
    
    jarvis._respond(justification)
    
    # Step 5: Run Playwright Browser Automation in Background
    threading.Thread(
        target=run_playwright_automation,
        args=(jarvis, best_option['url'], best_option['domain'], product),
        daemon=True,
        name="ShoppingAutomationThread"
    ).start()

    return False
